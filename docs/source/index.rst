.. ocr_translate documentation master file, created by
   sphinx-quickstart on Thu Sep 21 10:37:43 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ocr_translate's documentation!
=========================================

This is a Django app for creating back-end server aimed at performing OCR and translation of images received via a POST request.

The OCR and translation is performed using freely available machine learning models and packages (see below for what is currently implemented).

The server is designed to be used together with this browser `extension`_, acting as a front-end providing the images and controlling the model languages and models being used.

.. grid:: 2
      :gutter: 3

      .. grid-item-card:: Installation/Running

            Guide on installing and running ocr_translate with various methods.

            +++

            .. button-ref:: install_run/index
               :expand:
               :color: secondary
               :click-parent:

               Installation/Running Guides

      .. grid-item-card:: Running

            Guide on running ocr_translate from one of the installations.

            +++

            .. button-ref:: running/index
               :expand:
               :color: secondary
               :click-parent:

               Running Guides

      .. grid-item-card:: User Guides

         User guide for ocr_translate.

         +++

         .. button-ref:: user/index
            :expand:
            :color: secondary
            :click-parent:

            User Guides

      .. grid-item-card:: Contributor Guides

         Want to add to the codebase?
         The contributing guidelines will guide you through the
         process of improving ocr_translate.

         +++

         .. button-ref:: contrib/index
            :expand:
            :color: secondary
            :click-parent:

            Contributor guides

.. _extension: https://github.com/Crivella/ocr_extension

.. toctree::
   :hidden:

   install_run/index
   running/index
   user/index
   contrib/index
